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
- simple stylized illustrations as a lightweight fallback
- direct `custom_svg` rendering when the agent wants full visual control

This skill is **not** a photorealistic diffusion model. It is a local, rule-based composition engine that renders through SVG and exports PNG locally.

## When To Use It

Use `free-imagegen` when the request matches one or more of these cases:

- the user wants free local text-to-image generation
- the user wants local PNG output, with optional SVG retention when needed
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

## Decision Rules

Use these defaults unless the user clearly asks otherwise.

1. If the user gives a long article or says “turn this article into images”, prefer `--story-plan-file` when an agent can first read and plan the structure.
2. If the request is mostly text hierarchy and mobile readability, prefer `text_cover`.
3. If the request is explanation, comparison, workflow, grouped products, or knowledge transfer, prefer `infographic`.
4. If the request is a person, object, mascot, or scene that should be visually recognizable, prefer `custom_svg`.
5. Use `illustration` only as a fallback for quick stylized subject sketches.
6. If the user wants OpenClaw assets, use `--openclaw-project`.
7. Keep output mobile-readable whenever text density is high: fewer lines, larger text, simpler structure.
8. For long paragraphs that should stay close to the original writing, prefer `article_page` instead of forcing every section into an infographic layout.
9. Treat auto story generation as a draft/fallback. When quality matters, let the agent decide pagination and layout explicitly.

## Recommended Commands

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

### Keep SVG only when needed

Default behavior now writes PNG only to avoid clutter.

If you want source SVG files for debugging or manual editing, add:

```bash
--keep-svg
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

## Agent-First Workflow

When OpenClaw or another agent is available, prefer this sequence:

1. read the full article
2. decide pagination and layout page by page
3. write a `story-plan.json`
4. render with `--story-plan-file`

This keeps the high-judgment work in the agent and the rendering work in the skill.

Good uses for a plan file:

- a page should preserve original article paragraphs
- one section should become cards instead of prose
- the opening page should be an article page but the next page should be a mechanism card
- one page should use dark theme while another stays light
- the agent wants tighter or looser page density per page
- one page should feel more playful, with a little emoji/decor treatment, while another stays restrained

Per-page controls now supported in `story-plan.json`:

- `theme`
- `density`
- `surface_style` / `style`
- `accent`
- `series_style`
- `section_role`
- `tone`
- `decor_level`
- `emoji_policy`
- `emoji_render_mode`

Use `emoji_render_mode: "svg"` when the target environment is Linux/headless and emoji need to stay colorful and stable.

Recommended page types in a plan:

- `article_page`
- `text_cover`
- `mechanism`
- `checklist`
- `qa`
- `catalog`
- `map`
- `comparison`
- `flow`
- `timeline`

Recommended agent fields per page:

- `title`
- `subtitle`
- `kicker`
- `bullets`
- `emphasis`
- `image`
- `theme`
- `density`
- `series_style`
- `section_role`
- `surface_style`
- `accent`

## Input Guidance

### For story-plan workflows

Prefer letting the agent decide:

- where to split pages
- which sections stay as prose
- which sections become cards
- where to place images
- which visual treatment fits each page

Use the renderer as an execution engine, not as the only decision-maker.

If the agent emits an invalid `story-plan.json`, the CLI now stops early with a validation error and points back to the bundled template and schema.

### For article workflows

Prefer cleaned text input:

- keep headings
- keep bullet lists
- keep tables as text
- remove original embedded image placeholders
- keep important numbers, contrasts, and section labels

If an article has mixed content types, do not force one layout for the whole piece. Let the agent choose per page.

## Render Controls

The skill now exposes lightweight controls so the agent can steer look and density without editing code.

Global CLI controls:

- `--theme auto|light|dark`
- `--page-density auto|comfy|compact`
- `--surface-style auto|soft|card|minimal|editorial`
- `--accent auto|blue|green|warm|rose`

Per-page plan controls:

- `theme`
- `density`
- `series_style`
- `section_role`
- `surface_style` or `style`
- `accent`

Additional story-plan controls:

- `series_style: loose | unified`
- `section_role: cover | chapter | body | summary`

Use them like this:

- `series_style=loose`: let pages feel more independent
- `series_style=unified`: keep title spacing, section openers, and rhythm more aligned across `article_page`, `checklist`, `mechanism`, `catalog`, `qa`, `comparison`, `map`, `flow`, and `timeline`
- `section_role=chapter`: stronger section opener treatment
- `section_role=body`: normal reading page
- `section_role=summary`: stronger closing / takeaway rhythm

Important: these controls are still agent-authored decisions. The renderer should not invent them on its own.

Use them when the agent wants:

- dark pages for stronger contrast
- compact pages for dense lists
- comfy pages for article-like reading
- different accent colors for different sections
- different surface treatments across a card set

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
