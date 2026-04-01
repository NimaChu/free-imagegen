---
name: free-imagegen
description: Fully local free text-to-image skill for OpenClaw and general assets. Generates SVG from prompt, then converts SVG to PNG with local tools only (no online API calls).
---

# Free ImageGen

Use this skill when the user wants **fully local image generation** with a `Prompt -> SVG -> PNG` pipeline and does **not** want online image APIs.

This skill is best for:

- text-heavy cover images
- Xiaohongshu-style text covers
- infographics and knowledge cards
- article-to-image card sets
- OpenClaw thumbnails and icons
- simple stylized illustrations where editable SVG output matters

This skill is **not** a photorealistic diffusion model. It is a local, rule-based, SVG-first composition engine.

## When To Use It

Use `free-imagegen` when the request matches one or more of these cases:

- the user wants free local text-to-image generation
- the user wants SVG output plus PNG export
- the user wants a text cover, title card, poster, or thumbnail
- the user wants an infographic, comparison card, flow card, QA card, map, or catalog
- the user wants to turn an article into a sequence of image cards
- the user wants OpenClaw-ready `thumbnail` / `icon` assets

Do **not** use this skill when the user needs:

- photorealistic generation
- inpainting / outpainting
- model-based image editing
- online hosted image APIs

## Core Modes

Choose the mode from the user intent.

### `illustration`

Use for general drawing requests:

- characters
- objects
- scenes
- stylized posters without dense text

This is the default when the prompt is mostly about a subject rather than content structure.

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
- `01-cover.png/svg`
- `02-*.png/svg` and later cards

## Decision Rules

Use these defaults unless the user clearly asks otherwise.

1. If the user gives a long article or says “turn this article into images”, use `--prompt-file` plus `--story-output-dir`.
2. If the request is mostly text hierarchy and mobile readability, prefer `text_cover`.
3. If the request is explanation, comparison, workflow, grouped products, or knowledge transfer, prefer `infographic`.
4. If the request is a person, object, or scene, prefer `illustration`.
5. If the user wants OpenClaw assets, use `--openclaw-project`.
6. Keep output mobile-readable whenever text density is high: fewer lines, larger text, simpler structure.

## Recommended Commands

### Single image

```bash
python3 scripts/free_image_gen.py \
  --prompt "长发可爱女生，清新梦幻插画风，柔和光影，细节丰富" \
  --output /absolute/path/output/image.png \
  --svg-output /absolute/path/output/image.svg \
  --width 1024 \
  --height 1280
```

### Text cover

```bash
python3 scripts/free_image_gen.py \
  --prompt "文字封面，标题 AI 产品设计原则，副标题 清晰层级 高信息密度 强识别度，核心数字 07" \
  --output /absolute/path/output/text-cover.png \
  --svg-output /absolute/path/output/text-cover.svg \
  --width 1080 \
  --height 1440
```

### Infographic

```bash
python3 scripts/free_image_gen.py \
  --prompt "AI 编码工作流信息图，标题 GPT-5.4 Coding Workflow，副标题 从需求到提交，核心数字 4，1. 需求理解 2. 代码实现 3. 验证测试 4. 提交发布" \
  --output /absolute/path/output/infographic.png \
  --svg-output /absolute/path/output/infographic.svg \
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

### Analysis / prompts only

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --prompts-only
```

### Images only

```bash
python3 scripts/free_image_gen.py \
  --prompt-file /absolute/path/article.txt \
  --story-output-dir /absolute/path/output/article-story \
  --images-only
```

### OpenClaw assets

```bash
python3 scripts/free_image_gen.py \
  --prompt "space heist arcade lobster game" \
  --openclaw-project /absolute/path/to/your-openclaw-app
```

## Story Strategies

Use `--story-strategy` when article intent is clear.

- `auto`: default; let the tool infer the best structure
- `story`: narrative / experience / personal workflow
- `dense`: knowledge-heavy, structured, or terminology-heavy writing
- `visual`: lighter, more cover-like, less dense per card

## Input Guidance

### For article workflows

Prefer cleaned text input:

- keep headings
- keep bullet lists
- keep tables as text
- remove original embedded image placeholders
- keep important numbers, contrasts, and section labels

### For infographic prompts

Include as much structure as possible inside the prompt:

- title
- subtitle
- highlighted number
- bullets
- grouped items
- before/after language
- step order

### For text covers

Include the real copy directly in the prompt.

Good example:

- `文字封面，标题 Vibe Coding 产品地图，副标题 主流编码代理、AI IDE 与云端开发工具全景` 

### For illustrations

Describe:

- subject
- color
- mood
- lighting
- density of detail

## Output Expectations

When the task is text-heavy, optimize for:

- phone readability first
- fewer line breaks
- larger text when space allows
- simple hierarchy over decorative complexity
- stable layouts over overly clever compositions

When the task is article conversion, prefer a small set of clear cards over one overloaded image.

## HTTP Wrapper

Start local service:

```bash
python3 scripts/free_image_http_service.py --host 127.0.0.1 --port 8787
```

Endpoints:

- `/health`
- `/generate`
- `/openclaw-assets`

## Files

- `scripts/free_image_gen.py`: core SVG generation and PNG export
- `scripts/free_image_http_service.py`: local HTTP wrapper
- `references/providers.md`: renderer notes

## Practical Limits

Keep these in mind while using the skill:

- best results come from structured prompts
- article summarization is heuristic, not model-level semantic understanding
- illustration mode is stylized, not photorealistic
- final PNG fidelity depends on the local SVG renderer available on the machine
- some dense inputs may still need prompt cleanup for the cleanest mobile result
